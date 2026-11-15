//! Invoice archive: issued invoices are stored as JSON and read back for reprints.
use std::io;

use crate::domain::invoice::{Invoice, InvoiceNumber};
use crate::infra::fs_store::BlobStore;

#[derive(Debug, thiserror::Error)]
pub enum ArchiveError {
    #[error("could not encode invoice {number}")]
    Encode {
        number: InvoiceNumber,
        #[source]
        source: serde_json::Error,
    },
    #[error("could not store invoice {number}")]
    Store {
        number: InvoiceNumber,
        #[source]
        source: io::Error,
    },
}

/// Archives an issued invoice under its number.
pub fn archive<S: BlobStore>(store: &mut S, invoice: &Invoice) -> Result<(), ArchiveError> {
    let number = invoice.number();
    let bytes = serde_json::to_vec(invoice).map_err(|source| ArchiveError::Encode {
        number: number.clone(),
        source,
    })?;
    store.put(number.as_str(), &bytes).map_err(|source| ArchiveError::Store {
        number: number.clone(),
        source,
    })
}

/// Reads an archived invoice back; `None` when it was never archived.
pub fn load<S: BlobStore>(store: &S, number: &InvoiceNumber) -> Result<Option<Invoice>, serde_json::Error> {
    let Ok(Some(bytes)) = store.get(number.as_str()) else {
        return Ok(None);
    };
    serde_json::from_slice(&bytes).map(Some)
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;

    use super::*;
    use crate::domain::invoice::sample_invoice;

    #[derive(Debug, Default)]
    struct MemoryBlobStore(BTreeMap<String, Vec<u8>>);

    impl BlobStore for MemoryBlobStore {
        fn put(&mut self, key: &str, bytes: &[u8]) -> io::Result<()> {
            self.0.insert(key.to_owned(), bytes.to_vec());
            Ok(())
        }

        fn get(&self, key: &str) -> io::Result<Option<Vec<u8>>> {
            Ok(self.0.get(key).cloned())
        }
    }

    #[derive(Debug)]
    struct BrokenStore;

    impl BlobStore for BrokenStore {
        fn put(&mut self, _key: &str, _bytes: &[u8]) -> io::Result<()> {
            Err(io::Error::other("disk full"))
        }

        fn get(&self, _key: &str) -> io::Result<Option<Vec<u8>>> {
            Err(io::Error::other("disk unreadable"))
        }
    }

    #[test]
    fn a_failing_store_fails_the_archive() {
        assert!(matches!(archive(&mut BrokenStore, &sample_invoice()), Err(_)));
    }

    #[test]
    fn an_archived_invoice_loads_back() {
        let mut store = MemoryBlobStore::default();
        let invoice = sample_invoice();
        archive(&mut store, &invoice).unwrap();
        assert_eq!(load(&store, invoice.number()).unwrap(), Some(invoice));
    }

    #[test]
    fn an_unknown_number_is_none() {
        let store = MemoryBlobStore::default();
        assert_eq!(load(&store, sample_invoice().number()).unwrap(), None);
    }
}
