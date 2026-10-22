// The edge. clap parses each field through FromStr, so no value_parser is written.
use crate::domain::email::Email;
use crate::domain::port::{self, Port};

#[derive(Debug, clap::Parser)]
pub struct Cli {
    #[arg(long, env = "APP_EMAIL")]
    pub email: Email,
    // default_value_t prints the default with Display and parses it back through FromStr.
    #[arg(long, default_value_t = port::HTTP)]
    pub port: Port,
    #[arg(long, value_delimiter = ',')]
    pub cc: Vec<Email>,
}
