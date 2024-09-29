use pyo3::prelude::*;

mod protos;
mod tfs;

#[pymodule]
fn airflights(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(tfs::make_tfs, m)?)?;
    m.add_class::<tfs::Tfs>()?;
    Ok(())
}
