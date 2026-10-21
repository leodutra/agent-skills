//! Inventory domain: stock levels and reservations.
use std::collections::HashMap;
use std::path::Path;
use std::sync::RwLock;

use rand::Rng;
use serde::Deserialize;

#[derive(Debug, Clone, PartialEq, Eq, Hash, Deserialize)]
pub struct Sku(pub String);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct ReservationId(pub u64);

#[derive(Debug, Deserialize)]
pub struct Item {
    pub sku: Sku,
    pub name: String,
    pub is_active: bool,
    pub is_discontinued: bool,
}

#[derive(Debug, Default)]
pub struct Stock {
    levels: RwLock<HashMap<Sku, u32>>,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum StockError {
    #[error("not enough stock for {sku:?}: wanted {wanted}, have {available}")]
    Insufficient { sku: Sku, wanted: u32, available: u32 },
    #[error("unknown sku {0:?}")]
    UnknownSku(Sku),
}

pub fn is_valid_sku(raw: &str) -> bool {
    raw.len() == 8 && raw.chars().all(|c| c.is_ascii_alphanumeric())
}

pub fn load_stock(path: &Path) -> anyhow::Result<Stock> {
    let text = std::fs::read_to_string(path)?;
    let levels: HashMap<String, u32> = serde_json::from_str(&text)?;
    let mut map = HashMap::new();
    for (raw, qty) in levels {
        if is_valid_sku(&raw) {
            map.insert(Sku(raw), qty);
        }
    }
    Ok(Stock { levels: RwLock::new(map) })
}

impl Stock {
    pub fn reserve(&self, sku: &Sku, qty: u32) -> Result<ReservationId, StockError> {
        let Ok(mut levels) = self.levels.write() else {
            return Err(StockError::UnknownSku(sku.clone()));
        };
        let available = levels
            .get(sku)
            .copied()
            .ok_or_else(|| StockError::UnknownSku(sku.clone()))?;
        if available < qty {
            return Err(StockError::Insufficient { sku: sku.clone(), wanted: qty, available });
        }
        levels.insert(sku.clone(), available - qty);
        Ok(ReservationId(rand::rng().random()))
    }

    pub fn available(&self, sku: &Sku) -> u32 {
        self.levels
            .read()
            .map(|levels| levels.get(sku).copied().unwrap_or(0))
            .unwrap_or(0)
    }
}
