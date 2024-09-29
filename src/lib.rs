use pyo3::prelude::*;
use rand::Rng;

mod protos;
mod tfs;

#[pyfunction]
fn generate_trail() -> String {
    let lower = "abcdefghijklmnopqrstuvwxyz".to_string();
    let upper = lower.to_uppercase();
    let chars = lower + &upper;

    let mut rng = rand::thread_rng();
    let mut t = String::new();
    for _ in 0..10 {
        t.push(chars.chars().nth(rng.gen_range(0..chars.len())).unwrap());
    }

    t
}

#[pymodule]
fn airflights(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(generate_trail, m)?)?;
    m.add_function(wrap_pyfunction!(tfs::make_tfs, m)?)?;
    m.add_class::<tfs::Tfs>()?;
    Ok(())
}
