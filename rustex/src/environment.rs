// src/environment.rs
use dotenv::dotenv;
use std::env;

/// Struct to manage environment initialization and fetching
pub struct Env;

impl Env {
    /// Initializes environment variables based on the environment (e.g., development vs production)
    pub fn init() {
        match env::var("ENV") {
            Ok(env) if env == "production" => {
                panic!("Production environment not yet supported");
                // Production environment logic here, assume environment variables are injected
            }
            _ => {
                println!("Loading environment from .env file for development...");
                dotenv().ok(); // Load environment variables from `.env` file
            }
        }
    }

    /// Fetch an environment variable, or return an error if not found
    pub fn get(key: &str) -> Result<String, env::VarError> {
        env::var(key)
    }

    // /// Fetch an environment variable with a default value
    // pub fn get_or_default(key: &str, default: &str) -> String {
    //     env::var(key).unwrap_or_else(|_| default.to_string())
    // }
}
