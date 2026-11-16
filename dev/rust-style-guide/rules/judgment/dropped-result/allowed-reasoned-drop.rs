// keep: the reasoned #[expect] that drops the send result
use std::sync::mpsc::Sender;

/// Tells the progress bar, if one is still listening.
pub fn report_progress(progress: &Sender<u8>, percent: u8) {
    #[expect(clippy::let_underscore_must_use, reason = "the progress bar may already be closed")]
    let _ = progress.send(percent);
}
