// keep: the reasoned #[expect] that rebuilds the poisoned cache and clears the poison
#![expect(clippy::disallowed_types, reason = "infrastructure: the cache is shared across threads")]
use std::collections::BTreeMap;
use std::sync::{Mutex, MutexGuard};

/// A cache of rendered pages, shared by the server's worker threads (infrastructure, not domain).
#[derive(Debug, Default)]
pub struct PageCache {
    pages: Mutex<BTreeMap<String, String>>,
}

impl PageCache {
    /// The cache, emptied first if a panic poisoned it: nothing of the old pages is read.
    pub fn pages(&self) -> MutexGuard<'_, BTreeMap<String, String>> {
        match self.pages.lock() {
            Ok(pages) => pages,
            Err(poisoned) => {
                #[expect(clippy::disallowed_methods, reason = "rebuilds the whole value; the old data is dropped unread")]
                let mut pages = poisoned.into_inner();
                *pages = BTreeMap::new();
                self.pages.clear_poison();
                pages
            }
        }
    }
}
