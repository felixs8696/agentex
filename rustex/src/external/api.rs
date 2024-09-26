use actix_web::{get, App, HttpResponse, HttpServer, Responder};

#[get("/ask")]
async fn ask() -> impl Responder {
    HttpResponse::Ok().body("Hello world!")
}


pub async fn run() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new()
            .service(ask)
    })
        .bind(("127.0.0.1", 8080))?
        .run()
        .await
}
