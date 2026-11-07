use std::path::Path;

use inventory::domain::inventory::{load_stock, Sku, StockError};

#[test]
fn reserving_more_than_available_is_refused() {
    let stock = load_stock(Path::new("tests/fixtures/stock.json")).unwrap();
    let sku = Sku("AB12CD34".to_owned());
    let before = stock.available(&sku);
    let err = stock.reserve(&sku, before + 1).unwrap_err();
    assert_eq!(err, StockError::Insufficient { sku, wanted: before + 1, available: before });
}

#[test]
fn reserve_reduces_stock() {
    let stock = load_stock(Path::new("tests/fixtures/stock.json")).unwrap();
    let sku = Sku("AB12CD34".to_owned());
    let before = stock.available(&sku);
    stock.reserve(&sku, 1).unwrap();
    assert_eq!(stock.available(&sku), before - 1);
}
