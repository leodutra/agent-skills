pub async fn bump(counter: &mut u32) -> u32 {
    std::future::ready(()).await;
    *counter += 1;
    *counter
}
