mod environment;
mod external;

use environment::Env;

use crate::external::api;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    Env::init();
    api::run().await
}
