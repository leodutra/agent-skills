//! Exporting flushed metrics to a backend.
use std::io::{self, Write};

/// One metric value at flush time.
#[derive(Debug, Clone, PartialEq, serde::Serialize)]
pub struct Point {
    pub name: String,
    pub value: f64,
}

/// A metrics backend. Implement it to send batches anywhere: `Recorder::flush` calls `export`
/// with the points gathered since the last flush, in name order.
pub trait Exporter {
    /// Sends one batch; on error the recorder keeps the points for the next flush.
    fn export(&mut self, points: &[Point]) -> Result<(), ExportError>;
}

#[derive(Debug, thiserror::Error)]
#[non_exhaustive]
pub enum ExportError {
    #[error("the backend is unavailable")]
    Unavailable,
    #[error("could not write the batch")]
    Io(#[from] io::Error),
    #[error("could not encode the batch")]
    Encode(#[from] serde_json::Error),
}

/// Writes each batch as JSON lines, one point per line.
#[derive(Debug)]
pub struct JsonLinesExporter<W> {
    out: W,
}

impl<W: Write> JsonLinesExporter<W> {
    pub const fn new(out: W) -> Self {
        Self { out }
    }
}

impl<W: Write> Exporter for JsonLinesExporter<W> {
    fn export(&mut self, points: &[Point]) -> Result<(), ExportError> {
        for point in points {
            serde_json::to_writer(&mut self.out, point)?;
            self.out.write_all(b"\n")?;
        }
        Ok(self.out.flush()?)
    }
}
