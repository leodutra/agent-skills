//! The recorder: gathers the latest value per metric and flushes them in batches.
use std::collections::BTreeMap;
use std::fmt;
use std::num::NonZeroUsize;

use crate::export::{ExportError, Exporter, Point};

/// Decides when the recorder flushes.
pub(crate) trait FlushPolicy: fmt::Debug {
    fn should_flush(&self, pending: usize) -> bool;
}

/// Flush once `n` metrics are pending.
#[derive(Debug, Clone, Copy)]
pub(crate) struct EveryN(pub(crate) NonZeroUsize);

impl FlushPolicy for EveryN {
    fn should_flush(&self, pending: usize) -> bool {
        pending >= self.0.get()
    }
}

#[derive(Debug)]
pub struct Recorder<E> {
    exporter: E,
    policy: Box<dyn FlushPolicy>,
    pending: BTreeMap<String, f64>,
}

impl<E: Exporter> Recorder<E> {
    /// Flushes to `exporter` whenever `flush_every` metrics are pending; `None` if it is 0.
    pub fn new(exporter: E, flush_every: usize) -> Option<Self> {
        let every = NonZeroUsize::new(flush_every)?;
        Some(Self { exporter, policy: Box::new(EveryN(every)), pending: BTreeMap::new() })
    }

    /// Records the latest value of `name`, flushing if enough metrics are pending.
    pub fn record(&mut self, name: &str, value: f64) -> Result<(), ExportError> {
        self.pending.insert(name.to_owned(), value);
        if self.policy.should_flush(self.pending.len()) {
            self.flush()
        } else {
            Ok(())
        }
    }

    /// Sends every pending metric; they stay pending if the exporter fails.
    pub fn flush(&mut self) -> Result<(), ExportError> {
        let points: Vec<Point> = self
            .pending
            .iter()
            .map(|(name, value)| Point { name: name.clone(), value: *value })
            .collect();
        self.exporter.export(&points)?;
        self.pending.clear();
        Ok(())
    }
}
