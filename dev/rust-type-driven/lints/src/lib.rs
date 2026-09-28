//! Type-aware checks for `skills/rust-type-driven`: the rules clippy and ast-grep cannot see, because
//! they need to know what a type is, who implements a trait, or which function a call reaches.
//! Each lint names the rule it holds and the section of the skill it comes from.
#![feature(rustc_private)]
#![warn(unused_extern_crates)]

extern crate rustc_data_structures;
extern crate rustc_hir;
extern crate rustc_lint;
extern crate rustc_middle;
extern crate rustc_session;
extern crate rustc_span;

use clippy_utils::diagnostics::span_lint_and_help;
use rustc_data_structures::fx::FxHashSet;
use rustc_hir::def::DefKind;
use rustc_hir::def_id::{DefId, LocalDefId};
use rustc_hir::intravisit::FnKind;
use rustc_hir::attrs::lang_items::LangItem;
use rustc_hir::{Body, ClosureKind, CoroutineDesugaring, CoroutineKind, Expr, ExprKind, FnDecl, ItemKind, Node};
use clippy_utils::ty::implements_trait;
use rustc_lint::{LateContext, LateLintPass, LintContext};
use rustc_middle::ty::{self, Ty};
use rustc_span::{Span, sym};

dylint_linting::dylint_library!();

#[unsafe(no_mangle)]
pub fn register_lints(sess: &rustc_session::Session, lint_store: &mut rustc_lint::LintStore) {
    dylint_linting::init_config(sess);
    lint_store.register_lints(&[
        PUB_FIELD_ON_INVARIANT_TYPE,
        REFINEMENT_ESCAPE,
        ERROR_NOT_STD_ERROR,
        BLOCKING_IN_ASYNC,
        PRIMITIVE_DOMAIN_PARAM,
        SINGLE_IMPL_TRAIT,
    ]);
    lint_store.register_late_lint_pass(Box::new(|_| Box::new(RustTypeDriven)));
}

rustc_session::declare_lint! {
    /// A `pub` field on a type that has a fallible constructor (an associated fn without `self` returning
    /// `Result<Self, _>` or `Option<Self>`, or a `TryFrom` or `FromStr` impl): the constructor guards an
    /// invariant a struct literal can skip.
    /// Holds Type-Driven Design: a refinement's fields "MUST be private"; a `pub` field declares a tag.
    pub PUB_FIELD_ON_INVARIANT_TYPE,
    Warn,
    "a public field on a type with a fallible constructor"
}

rustc_session::declare_lint! {
    /// On a type with a fallible constructor: an impl of `Deref`, `DerefMut`, `AsMut` or `BorrowMut`, or a
    /// public method returning `&mut`. Each hands out the inner value past the constructor's checks.
    /// Holds Newtypes, Invariant integrity: "It MUST NOT hand out `&mut` to its inner value, nor implement
    /// `Deref` or `DerefMut`".
    pub REFINEMENT_ESCAPE,
    Warn,
    "a refinement that hands out its inner value"
}

rustc_session::declare_lint! {
    /// An error type that does not implement `std::error::Error + Send + Sync`: `()`, or a type of this
    /// crate, as the error of a public fn's `Result`, or as a `FromStr` or `TryFrom` impl's error.
    /// Holds Error Modeling: "an error type implements `std::error::Error + Send + Sync + 'static`".
    pub ERROR_NOT_STD_ERROR,
    Warn,
    "an error type that is not a std error"
}

rustc_session::declare_lint! {
    /// A call that blocks the thread (`std::fs`, `std::net`, `std::thread::sleep`, `std::process` waits,
    /// stdin) inside an `async fn` or `async` block, outside a closure such as `spawn_blocking`'s.
    /// Holds Async, Blocking work: "Async code MUST NOT block the runtime."
    pub BLOCKING_IN_ASYNC,
    Warn,
    "a blocking call inside async code"
}

rustc_session::declare_lint! {
    /// A heuristic: a public fn in a `domain` module taking a primitive (`String`, `&str`, an integer,
    /// `uuid::Uuid`) for a parameter named like a domain concept (`id`, `*_id`, `email`, `name`, `amount`).
    /// Holds Type-Driven Design: a value with an invariant, or one that could be swapped with another
    /// of the same primitive, gets a newtype.
    pub PRIMITIVE_DOMAIN_PARAM,
    Warn,
    "a raw primitive naming a domain concept in a public domain signature"
}

rustc_session::declare_lint! {
    /// A trait that is not exported from the crate and has exactly one implementation, test doubles
    /// included. Runs only when the crate is compiled for tests (`--all-targets`), where `#[cfg(test)]`
    /// doubles exist.
    /// Holds Dependency Injection: "A trait SHOULD NOT be introduced for a single implementation unless a
    /// real second implementation or test double is needed."
    pub SINGLE_IMPL_TRAIT,
    Warn,
    "a crate-local trait with a single implementation and no test double"
}

rustc_session::declare_lint_pass!(RustTypeDriven => [
    PUB_FIELD_ON_INVARIANT_TYPE,
    REFINEMENT_ESCAPE,
    ERROR_NOT_STD_ERROR,
    BLOCKING_IN_ASYNC,
    PRIMITIVE_DOMAIN_PARAM,
    SINGLE_IMPL_TRAIT,
]);

/// Traits whose impls hand out a type's inner value, by path; `Deref` and `DerefMut` are lang items.
const ESCAPES: &[&str] = &["convert::AsMut", "borrow::BorrowMut"];

/// Paths whose calls block the thread; a prefix ending in `::` covers the whole module.
const BLOCKING: &[&str] = &[
    "std::fs::",
    "std::net::",
    "std::thread::sleep",
    "std::process::Command::output",
    "std::process::Command::status",
    "std::process::Child::wait",
    "std::io::stdin",
];

/// Parameter names that stand for a domain concept.
fn names_a_domain_concept(name: &str) -> bool {
    name == "id" || name.ends_with("_id") || matches!(name, "email" | "name" | "amount")
}

impl<'tcx> LateLintPass<'tcx> for RustTypeDriven {
    fn check_crate_post(&mut self, cx: &LateContext<'tcx>) {
        let tcx = cx.tcx;
        // Types with a TryFrom or FromStr impl: both are fallible constructors.
        let mut fallible: FxHashSet<DefId> = FxHashSet::default();
        if let Some(try_from) = tcx.get_diagnostic_item(sym::TryFrom) {
            for impl_id in tcx.all_impls(try_from) {
                let self_ty = tcx.impl_trait_ref(impl_id).instantiate_identity().skip_norm_wip().self_ty();
                if let Some(adt) = self_ty.ty_adt_def() {
                    fallible.insert(adt.did());
                }
            }
        }
        // Local FromStr and TryFrom impls: their error types are checked too.
        let mut conversions = Vec::new();
        for item_id in tcx.hir_free_items() {
            // FromStr has no diagnostic item to look up, so the crate's own trait impls are matched by path
            let impl_id = item_id.owner_id.to_def_id();
            if matches!(tcx.def_kind(impl_id), DefKind::Impl { of_trait: true }) {
                let trait_ref = tcx.impl_trait_ref(impl_id).instantiate_identity().skip_norm_wip();
                let from_str = matches!(tcx.def_path_str(trait_ref.def_id).as_str(), "std::str::FromStr" | "core::str::FromStr");
                if from_str && let Some(adt) = trait_ref.self_ty().ty_adt_def() {
                    fallible.insert(adt.did());
                }
                if from_str || tcx.is_diagnostic_item(sym::TryFrom, trait_ref.def_id) {
                    conversions.push(impl_id);
                }
            }
        }
        let guarded = |def_id: DefId| {
            fallible.contains(&def_id)
                || tcx.inherent_impls(def_id).iter().any(|&imp| {
                    tcx.associated_items(imp)
                        .in_definition_order()
                        .any(|assoc| !assoc.is_method() && returns_fallible_self(cx, assoc.def_id, def_id))
                })
        };
        for item_id in tcx.hir_free_items() {
            let item = tcx.hir_item(item_id);
            let def_id = item.owner_id.to_def_id();
            match item.kind {
                ItemKind::Struct(..) if guarded(def_id) => {
                    for field in tcx.adt_def(def_id).all_fields() {
                        if field.vis.is_public() {
                            span_lint_and_help(
                                cx,
                                PUB_FIELD_ON_INVARIANT_TYPE,
                                tcx.def_span(field.did),
                                "a public field on a type with a fallible constructor",
                                None,
                                "make it private: the constructor is the only way in (Type-Driven Design)",
                            );
                        }
                    }
                    for &imp in tcx.inherent_impls(def_id) {
                        for assoc in tcx.associated_items(imp).in_definition_order() {
                            let returns_mut = assoc.is_method()
                                && tcx.visibility(assoc.def_id).is_public()
                                && matches!(
                                    tcx.fn_sig(assoc.def_id).instantiate_identity().skip_norm_wip().skip_binder().output().kind(),
                                    ty::Ref(_, _, ty::Mutability::Mut)
                                );
                            if returns_mut {
                                span_lint_and_help(
                                    cx,
                                    REFINEMENT_ESCAPE,
                                    tcx.def_span(assoc.def_id),
                                    "a public method hands out `&mut` past the constructor's checks",
                                    None,
                                    "offer a method that keeps the invariant, or none (Newtypes, Invariant integrity)",
                                );
                            }
                        }
                    }
                },
                ItemKind::Impl(..) if matches!(tcx.def_kind(def_id), DefKind::Impl { of_trait: true }) => {
                    let trait_ref = tcx.impl_trait_ref(def_id).instantiate_identity().skip_norm_wip();
                    let lang = tcx.lang_items();
                    let path = tcx.def_path_str(trait_ref.def_id);
                    let escapes = lang.deref_trait() == Some(trait_ref.def_id)
                        || lang.deref_mut_trait() == Some(trait_ref.def_id)
                        || ESCAPES.iter().any(|p| path == format!("std::{p}") || path == format!("core::{p}"));
                    if escapes && trait_ref.self_ty().ty_adt_def().is_some_and(|adt| guarded(adt.did())) {
                        span_lint_and_help(
                            cx,
                            REFINEMENT_ESCAPE,
                            tcx.def_span(def_id),
                            format!("`{path}` hands out the inner value past the constructor's checks"),
                            None,
                            "offer as_str(), get(), AsRef or into_inner() instead (Newtypes, Invariant integrity)",
                        );
                    }
                },
                ItemKind::Trait { .. }
                    if cx.sess().opts.test && !cx.effective_visibilities.is_exported(item.owner_id.def_id) =>
                {
                    if tcx.all_impls(def_id).count() == 1 {
                        span_lint_and_help(
                            cx,
                            SINGLE_IMPL_TRAIT,
                            tcx.def_span(def_id),
                            "a trait with a single implementation and no test double",
                            None,
                            "call the implementation directly, or add the double that justifies the trait (Dependency Injection)",
                        );
                    }
                },
                _ => {},
            }
        }
        for impl_id in conversions {
            for assoc in tcx.associated_items(impl_id).in_definition_order() {
                if matches!(assoc.kind, ty::AssocKind::Type { .. }) {
                    let error = tcx.type_of(assoc.def_id).instantiate_identity().skip_norm_wip();
                    check_error_type(cx, error, tcx.def_span(assoc.def_id));
                }
            }
        }
    }

    fn check_expr(&mut self, cx: &LateContext<'tcx>, expr: &'tcx Expr<'tcx>) {
        let callee = match expr.kind {
            ExprKind::Call(func, _) => match func.kind {
                ExprKind::Path(ref qpath) => cx.qpath_res(qpath, func.hir_id).opt_def_id(),
                _ => None,
            },
            ExprKind::MethodCall(..) => cx.typeck_results().type_dependent_def_id(expr.hir_id),
            _ => None,
        };
        let Some(callee) = callee else { return };
        let path = cx.tcx.def_path_str(callee);
        if !BLOCKING.iter().any(|p| path.starts_with(p)) {
            return;
        }
        // The nearest enclosing closure decides: an async body is one; spawn_blocking's closure is not.
        for (_, node) in cx.tcx.hir_parent_iter(expr.hir_id) {
            if let Node::Expr(parent) = node
                && let ExprKind::Closure(closure) = parent.kind
            {
                if matches!(
                    closure.kind,
                    ClosureKind::Coroutine(CoroutineKind::Desugared(CoroutineDesugaring::Async, _))
                ) {
                    span_lint_and_help(
                        cx,
                        BLOCKING_IN_ASYNC,
                        expr.span,
                        format!("`{path}` blocks the thread inside async code"),
                        None,
                        "use the async equivalent, or move it into spawn_blocking (Async, Blocking work)",
                    );
                }
                return;
            }
        }
    }

    fn check_fn(
        &mut self,
        cx: &LateContext<'tcx>,
        kind: FnKind<'tcx>,
        decl: &'tcx FnDecl<'_>,
        body: &'tcx Body<'_>,
        _: Span,
        def_id: LocalDefId,
    ) {
        if !matches!(kind, FnKind::ItemFn(..) | FnKind::Method(..)) || !cx.tcx.visibility(def_id).is_public() {
            return;
        }
        let sig = cx.tcx.fn_sig(def_id).instantiate_identity().skip_norm_wip();
        let in_trait_impl = matches!(cx.tcx.def_kind(cx.tcx.parent(def_id.to_def_id())), DefKind::Impl { of_trait: true });
        if !in_trait_impl  // a trait impl's error is its associated type, checked in check_crate_post
            && let ty::Adt(result, args) = sig.skip_binder().output().kind()
            && cx.tcx.is_diagnostic_item(sym::Result, result.did())
        {
            check_error_type(cx, args.type_at(1), decl.output.span());
        }
        if !cx.tcx.def_path_str(def_id.to_def_id()).split("::").any(|segment| segment == "domain") {
            return;
        }
        for (param, param_ty) in body.params.iter().zip(sig.skip_binder().inputs()) {
            let Some(ident) = param.pat.simple_ident() else { continue };
            if !names_a_domain_concept(ident.as_str()) {
                continue;
            }
            let t = param_ty.peel_refs();
            let primitive = t.is_str()
                || t.is_integral()
                || matches!(t.kind(), ty::Adt(adt, _)
                    if cx.tcx.is_lang_item(adt.did(), LangItem::String)
                        || (cx.tcx.crate_name(adt.did().krate).as_str() == "uuid" && cx.tcx.item_name(adt.did()).as_str() == "Uuid"));
            if primitive {
                span_lint_and_help(
                    cx,
                    PRIMITIVE_DOMAIN_PARAM,
                    param.span,
                    format!("`{ident}` is a raw `{t}` in a public domain signature"),
                    None,
                    "give the concept a newtype that parses once (Type-Driven Design)",
                );
            }
        }
    }
}

/// Whether `fn_id` is an associated fn returning `Result<Adt, _>` or `Option<Adt>` for the given type.
fn returns_fallible_self(cx: &LateContext<'_>, fn_id: DefId, adt_id: DefId) -> bool {
    if cx.tcx.def_kind(fn_id) != DefKind::AssocFn {
        return false;
    }
    let output = cx.tcx.fn_sig(fn_id).instantiate_identity().skip_norm_wip().skip_binder().output();
    matches!(output.kind(), ty::Adt(wrapper, args)
        if (cx.tcx.is_diagnostic_item(sym::Result, wrapper.did()) || cx.tcx.is_diagnostic_item(sym::Option, wrapper.did()))
            && args.type_at(0).ty_adt_def().is_some_and(|adt| adt.did() == adt_id))
}

/// Lints `error` when it is `()`, or a type of this crate that is not `std::error::Error + Send + Sync`.
fn check_error_type<'tcx>(cx: &LateContext<'tcx>, error: Ty<'tcx>, span: Span) {
    let tcx = cx.tcx;
    let is_std_error = |t: Ty<'tcx>| {
        [tcx.get_diagnostic_item(clippy_utils::sym::Error), tcx.get_diagnostic_item(sym::Send), tcx.lang_items().sync_trait()]
            .into_iter()
            .all(|tr| tr.is_some_and(|tr| implements_trait(cx, t, tr, &[])))
    };
    let bad = match error.kind() {
        ty::Tuple(fields) => fields.is_empty(),
        ty::Adt(adt, _) => adt.did().is_local() && !is_std_error(error),
        _ => false,
    };
    if bad {
        span_lint_and_help(
            cx,
            ERROR_NOT_STD_ERROR,
            span,
            format!("`{error}` is an error type that is not `std::error::Error + Send + Sync`"),
            None,
            "derive thiserror::Error on an enum of the reasons (Error Modeling)",
        );
    }
}
