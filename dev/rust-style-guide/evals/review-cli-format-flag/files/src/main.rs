//! `stockctl export`: prints the inventory snapshot in the format the caller picks.
use std::fmt;
use std::str::FromStr;
use std::path::PathBuf;

use anyhow::Context;
use clap::Parser;
use stock::Snapshot;

/// An export format name, checked against the formats we support.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FormatName(String);

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[error("unknown format {0:?}: expected json, csv or table")]
pub struct UnknownFormat(String);

const SUPPORTED: [&str; 3] = ["json", "csv", "table"];

impl FormatName {
    pub fn try_new(raw: &str) -> Result<Self, UnknownFormat> {
        let name = raw.trim().to_ascii_lowercase();
        if SUPPORTED.contains(&name.as_str()) {
            Ok(Self(name))
        } else {
            Err(UnknownFormat(raw.to_owned()))
        }
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl fmt::Display for FormatName {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

/// Row order for csv and table output; stockctl.toml's `[export] sort` uses the same names.
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum SortKey {
    Sku,
    Quantity,
    Value,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[error("unknown sort key {0:?}: expected sku, qty or value")]
pub struct UnknownSortKey(String);

impl FromStr for SortKey {
    type Err = UnknownSortKey;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "sku" => Ok(Self::Sku),
            "qty" => Ok(Self::Quantity),
            "value" => Ok(Self::Value),
            other => Err(UnknownSortKey(other.to_owned())),
        }
    }
}

#[derive(Debug, Parser)]
#[command(name = "stockctl", about = "Export the inventory snapshot")]
struct Args {
    /// Snapshot file to read.
    #[arg(long)]
    snapshot: PathBuf,
    /// Output format: json, csv or table.
    #[arg(long, default_value = "table", value_parser = FormatName::try_new)]
    format: FormatName,
    /// Row order: sku, qty or value.
    #[arg(long, default_value = "sku")]
    sort: SortKey,
}

fn render(snapshot: &Snapshot, format: &FormatName, sort: SortKey) -> anyhow::Result<String> {
    match format.as_str() {
        "json" => Ok(serde_json::to_string_pretty(snapshot)?),
        "csv" => Ok(stock::render::csv(snapshot, sort)),
        _ => Ok(stock::render::table(snapshot, sort)),
    }
}

#[expect(clippy::print_stdout, reason = "the export is this program's output")]
fn main() -> anyhow::Result<()> {
    let args = Args::parse();
    let snapshot = Snapshot::load(&args.snapshot)
        .with_context(|| format!("reading snapshot {}", args.snapshot.display()))?;
    println!("{}", render(&snapshot, &args.format, args.sort)?);
    Ok(())
}
