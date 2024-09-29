use std::collections::HashMap;

use base64_light::base64_encode_bytes;
use pyo3::{prelude::*, types::PyBytes};
use quick_protobuf::serialize_into_vec;

use crate::protos::flights as flights_mod;

#[pyclass]
pub struct Tfs {
    data: flights_mod::Tfs,
    bytes: Vec<u8>,
}

#[pymethods]
impl Tfs {
    fn __repr__(&self) -> String {
        format!("Tfs(data={:?}, bytes={:?})", self.data, self.bytes)
    }

    fn bytes(&self, py: Python) -> Py<PyAny> {
        PyBytes::new_bound(py, &self.bytes).into()
    }

    fn base64(&self) -> String {
        base64_encode_bytes(&self.bytes)
    }
}

#[pyfunction]
pub fn make_tfs(
    py: Python,
    flights_data: Vec<HashMap<String, Py<PyAny>>>,
    seat_data: String,
    passengers_data: Vec<Py<PyAny>>,
    trip_data: String,
) -> PyResult<Tfs> {
    // Process flight data
    let mut flights: Vec<flights_mod::FlightData> = vec![];

    for flight in flights_data {
        let mut data = flights_mod::FlightData::default();
        for (key, value) in flight {
            match key.as_str() {
                "date" => data.date = value.extract::<String>(py)?,
                "from" => {
                    data.from = Some(flights_mod::Airport {
                        name: value.extract::<String>(py)?,
                    })
                }
                "to" => {
                    data.to = Some(flights_mod::Airport {
                        name: value.extract::<String>(py)?,
                    })
                }
                _ => return Err(PyErr::new::<pyo3::exceptions::PyKeyError, _>(key)),
            }
        }
        flights.push(data);
    }

    // Process passengers
    let mut passengers: Vec<flights_mod::Passenger> = vec![];
    for passenger in passengers_data {
        match passenger.extract::<String>(py)?.as_str() {
            "adult" => passengers.push(flights_mod::Passenger::ADULT),
            "child" => passengers.push(flights_mod::Passenger::CHILD),
            "infant_in_seat" => passengers.push(flights_mod::Passenger::INFANT_IN_SEAT),
            "infant_on_lap" => passengers.push(flights_mod::Passenger::INFANT_ON_LAP),
            _ => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                    "Unknown passenger name {}",
                    passenger
                )))
            }
        }
    }

    // Process seat
    let seat = match seat_data.as_str() {
        "economy" => flights_mod::Seat::ECONOMY,
        "premium_economy" => flights_mod::Seat::PREMIUM_ECONOMY,
        "business" => flights_mod::Seat::BUSINESS,
        "first" => flights_mod::Seat::FIRST,
        _ => {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Unknown seat name {}",
                seat_data
            )))
        }
    };

    // Process trip
    let trip = match trip_data.as_str() {
        "round_trip" => flights_mod::Trip::ROUND_TRIP,
        "one_way" => flights_mod::Trip::ONE_WAY,
        "multi_city" => flights_mod::Trip::MULTI_CITY,
        _ => {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Unknown trip name {}",
                trip_data
            )))
        }
    };

    // Process TFS
    let tfs = flights_mod::Tfs {
        data: flights,
        passengers,
        seat,
        trip,
    };

    match serialize_into_vec(&tfs) {
        Ok(bytes) => Ok(Tfs { data: tfs, bytes }),
        Err(e) => Err(pyo3::exceptions::PyRuntimeError::new_err(format!("{}", e))),
    }
}
