pub fn copy_into(items: &[u32], out: &mut Vec<u32>) {
    for item in items {
        out.push(*item);
    }
}
