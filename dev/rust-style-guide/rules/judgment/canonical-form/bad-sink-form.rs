/// A comment's text, escaped for HTML at construction so every page can print it directly.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct CommentBody(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct EmptyComment;

impl CommentBody {
    /// # Errors
    /// [`EmptyComment`] when `raw` is blank.
    pub fn try_new(raw: &str) -> Result<Self, EmptyComment> {
        let text = raw.trim();
        if text.is_empty() {
            return Err(EmptyComment);
        }
        Ok(Self(text.replace('&', "&amp;").replace('<', "&lt;").replace('>', "&gt;")))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}
