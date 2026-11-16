**Proportionality**: a newtype, trait, error variant, layer or generic parameter exists only when it
enforces an invariant, prevents a real misuse, names a domain concept or measurably eases
maintenance; never for uniformity.

A trait exists only for a real abstraction need: a second implementation, a test double, outside
implementors, a generic algorithm, or methods on a foreign type (an extension trait, named `…Ext`);
never for flexibility nobody uses yet.

Question: does this code add a newtype, trait, error variant, layer or generic parameter that none
of these needs justify?
