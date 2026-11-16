// expect: clippy::needless_for_each
pub fn copy_into(items: &[u32], out: &mut Vec<u32>) {
    items.iter().for_each(|item| {
        out.push(*item);
    });
}
