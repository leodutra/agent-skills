//! The weekly team summary as fixed-width text.

/// One line of the summary: who, and how many tickets they closed this week.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Row {
    pub name: String,
    pub closed: u32,
}

/// Renders `rows`, most tickets first, each name cut to `width` columns, then the total.
#[must_use]
pub fn render(title: &str, rows: &[Row], width: usize) -> String {
    let mut sorted: Vec<&Row> = rows.iter().collect();
    sorted.sort_by(|a, b| b.closed.cmp(&a.closed).then_with(|| a.name.cmp(&b.name)));

    let mut out = format!("{title}\n");
    for row in sorted {
        let name = if row.name.len() > width { row.name.split_at(width).0 } else { row.name.as_str() };
        out.push_str(&format!("{name:<width$} {:>5}\n", row.closed));
    }
    out.push_str(&format!("{:<width$} {:>5}\n", "total", total(rows)));
    out
}

/// Tickets closed by the whole team.
#[must_use]
pub fn total(rows: &[Row]) -> u64 {
    rows.iter().map(|row| u64::from(row.closed)).sum()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn most_tickets_first_then_total() {
        let rows = [
            Row { name: "ana".to_owned(), closed: 3 },
            Row { name: "bruno".to_owned(), closed: 7 },
        ];
        assert_eq!(render("week 12", &rows, 6), "week 12\nbruno      7\nana        3\ntotal     10\n");
    }
}
