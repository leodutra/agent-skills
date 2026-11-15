//! Postage: which carrier can take a parcel, and what it costs.

/// A parcel as the counter clerk weighs it.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Parcel {
    weight: u32,
}

impl Parcel {
    /// The counter scale reads whole grams.
    #[must_use]
    pub const fn from_grams(grams: u32) -> Self {
        Self { weight: grams }
    }

    #[must_use]
    pub const fn weight(self) -> u32 {
        self.weight
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Carrier {
    Courier,
    Freight,
}

impl Carrier {
    /// Heaviest parcel the carrier takes, in ounces, from its US rate sheet.
    #[must_use]
    pub const fn max_weight(self) -> u32 {
        match self {
            Self::Courier => 1_120,
            Self::Freight => 2_400,
        }
    }

    /// Weight up to which the base price applies, in ounces.
    #[must_use]
    pub const fn price_break(self) -> u32 {
        match self {
            Self::Courier => 16,
            Self::Freight => 160,
        }
    }

    #[must_use]
    pub const fn base_cents(self) -> u64 {
        match self {
            Self::Courier => 899,
            Self::Freight => 4_500,
        }
    }

    #[must_use]
    pub const fn cents_per_extra_ounce(self) -> u64 {
        match self {
            Self::Courier => 35,
            Self::Freight => 12,
        }
    }
}

/// Whole ounces, rounded down as the rate sheets do.
#[must_use]
pub const fn grams_to_ounces(grams: u32) -> u32 {
    grams / 28
}

/// Whether the carrier accepts the parcel at all.
#[must_use]
pub const fn fits(parcel: Parcel, carrier: Carrier) -> bool {
    parcel.weight() <= carrier.max_weight()
}

/// Price in cents for a parcel the carrier accepts.
#[must_use]
pub fn price_cents(parcel: Parcel, carrier: Carrier) -> u64 {
    let ounces = grams_to_ounces(parcel.weight());
    let extra = ounces.saturating_sub(carrier.price_break());
    carrier.base_cents() + u64::from(extra) * carrier.cents_per_extra_ounce()
}

/// The weight line printed on the label.
#[must_use]
pub fn label_weight(parcel: Parcel) -> String {
    format!("{} oz", grams_to_ounces(parcel.weight()))
}
