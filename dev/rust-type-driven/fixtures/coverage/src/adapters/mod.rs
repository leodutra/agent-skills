// Outside the domain path: its rejections are not listed.
pub fn open(path: &str) -> Result<(), std::io::Error> {
    if path.is_empty() {
        return Err(std::io::Error::other("empty path"));
    }
    Ok(())
}
