// Automatically generated rust module for 'flights.proto' file

#![allow(non_snake_case)]
#![allow(non_upper_case_globals)]
#![allow(non_camel_case_types)]
#![allow(unused_imports)]
#![allow(unknown_lints)]
#![allow(clippy::all)]
#![cfg_attr(rustfmt, rustfmt_skip)]


use quick_protobuf::{MessageInfo, MessageRead, MessageWrite, BytesReader, Writer, WriterBackend, Result};
use quick_protobuf::sizeofs::*;
use super::*;

#[derive(Debug, PartialEq, Eq, Clone, Copy)]
pub enum Seat {
    ECONOMY = 1,
    PREMIUM_ECONOMY = 2,
    BUSINESS = 3,
    FIRST = 4,
}

impl Default for Seat {
    fn default() -> Self {
        Seat::ECONOMY
    }
}

impl From<i32> for Seat {
    fn from(i: i32) -> Self {
        match i {
            1 => Seat::ECONOMY,
            2 => Seat::PREMIUM_ECONOMY,
            3 => Seat::BUSINESS,
            4 => Seat::FIRST,
            _ => Self::default(),
        }
    }
}

impl<'a> From<&'a str> for Seat {
    fn from(s: &'a str) -> Self {
        match s {
            "ECONOMY" => Seat::ECONOMY,
            "PREMIUM_ECONOMY" => Seat::PREMIUM_ECONOMY,
            "BUSINESS" => Seat::BUSINESS,
            "FIRST" => Seat::FIRST,
            _ => Self::default(),
        }
    }
}

#[derive(Debug, PartialEq, Eq, Clone, Copy)]
pub enum Trip {
    ROUND_TRIP = 1,
    ONE_WAY = 2,
    MULTI_CITY = 3,
}

impl Default for Trip {
    fn default() -> Self {
        Trip::ROUND_TRIP
    }
}

impl From<i32> for Trip {
    fn from(i: i32) -> Self {
        match i {
            1 => Trip::ROUND_TRIP,
            2 => Trip::ONE_WAY,
            3 => Trip::MULTI_CITY,
            _ => Self::default(),
        }
    }
}

impl<'a> From<&'a str> for Trip {
    fn from(s: &'a str) -> Self {
        match s {
            "ROUND_TRIP" => Trip::ROUND_TRIP,
            "ONE_WAY" => Trip::ONE_WAY,
            "MULTI_CITY" => Trip::MULTI_CITY,
            _ => Self::default(),
        }
    }
}

#[derive(Debug, PartialEq, Eq, Clone, Copy)]
pub enum Passenger {
    ADULT = 1,
    CHILD = 2,
    INFANT_IN_SEAT = 3,
    INFANT_ON_LAP = 4,
}

impl Default for Passenger {
    fn default() -> Self {
        Passenger::ADULT
    }
}

impl From<i32> for Passenger {
    fn from(i: i32) -> Self {
        match i {
            1 => Passenger::ADULT,
            2 => Passenger::CHILD,
            3 => Passenger::INFANT_IN_SEAT,
            4 => Passenger::INFANT_ON_LAP,
            _ => Self::default(),
        }
    }
}

impl<'a> From<&'a str> for Passenger {
    fn from(s: &'a str) -> Self {
        match s {
            "ADULT" => Passenger::ADULT,
            "CHILD" => Passenger::CHILD,
            "INFANT_IN_SEAT" => Passenger::INFANT_IN_SEAT,
            "INFANT_ON_LAP" => Passenger::INFANT_ON_LAP,
            _ => Self::default(),
        }
    }
}

#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Debug, Default, PartialEq, Clone)]
pub struct Airport {
    pub name: String,
}

impl<'a> MessageRead<'a> for Airport {
    fn from_reader(r: &mut BytesReader, bytes: &'a [u8]) -> Result<Self> {
        let mut msg = Self::default();
        while !r.is_eof() {
            match r.next_tag(bytes) {
                Ok(18) => msg.name = r.read_string(bytes)?.to_owned(),
                Ok(t) => { r.read_unknown(bytes, t)?; }
                Err(e) => return Err(e),
            }
        }
        Ok(msg)
    }
}

impl MessageWrite for Airport {
    fn get_size(&self) -> usize {
        0
        + if self.name == String::default() { 0 } else { 1 + sizeof_len((&self.name).len()) }
    }

    fn write_message<W: WriterBackend>(&self, w: &mut Writer<W>) -> Result<()> {
        if self.name != String::default() { w.write_with_tag(18, |w| w.write_string(&**&self.name))?; }
        Ok(())
    }
}

#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Debug, Default, PartialEq, Clone)]
pub struct FlightData {
    pub date: String,
    pub from: Option<flights::Airport>,
    pub to: Option<flights::Airport>,
}

impl<'a> MessageRead<'a> for FlightData {
    fn from_reader(r: &mut BytesReader, bytes: &'a [u8]) -> Result<Self> {
        let mut msg = Self::default();
        while !r.is_eof() {
            match r.next_tag(bytes) {
                Ok(18) => msg.date = r.read_string(bytes)?.to_owned(),
                Ok(106) => msg.from = Some(r.read_message::<flights::Airport>(bytes)?),
                Ok(114) => msg.to = Some(r.read_message::<flights::Airport>(bytes)?),
                Ok(t) => { r.read_unknown(bytes, t)?; }
                Err(e) => return Err(e),
            }
        }
        Ok(msg)
    }
}

impl MessageWrite for FlightData {
    fn get_size(&self) -> usize {
        0
        + if self.date == String::default() { 0 } else { 1 + sizeof_len((&self.date).len()) }
        + self.from.as_ref().map_or(0, |m| 1 + sizeof_len((m).get_size()))
        + self.to.as_ref().map_or(0, |m| 1 + sizeof_len((m).get_size()))
    }

    fn write_message<W: WriterBackend>(&self, w: &mut Writer<W>) -> Result<()> {
        if self.date != String::default() { w.write_with_tag(18, |w| w.write_string(&**&self.date))?; }
        if let Some(ref s) = self.from { w.write_with_tag(106, |w| w.write_message(s))?; }
        if let Some(ref s) = self.to { w.write_with_tag(114, |w| w.write_message(s))?; }
        Ok(())
    }
}

#[allow(clippy::derive_partial_eq_without_eq)]
#[derive(Debug, Default, PartialEq, Clone)]
pub struct Tfs {
    pub data: Vec<flights::FlightData>,
    pub seat: flights::Seat,
    pub passengers: Vec<flights::Passenger>,
    pub trip: flights::Trip,
}

impl<'a> MessageRead<'a> for Tfs {
    fn from_reader(r: &mut BytesReader, bytes: &'a [u8]) -> Result<Self> {
        let mut msg = Self::default();
        while !r.is_eof() {
            match r.next_tag(bytes) {
                Ok(26) => msg.data.push(r.read_message::<flights::FlightData>(bytes)?),
                Ok(72) => msg.seat = r.read_enum(bytes)?,
                Ok(66) => msg.passengers = r.read_packed(bytes, |r, bytes| Ok(r.read_enum(bytes)?))?,
                Ok(152) => msg.trip = r.read_enum(bytes)?,
                Ok(t) => { r.read_unknown(bytes, t)?; }
                Err(e) => return Err(e),
            }
        }
        Ok(msg)
    }
}

impl MessageWrite for Tfs {
    fn get_size(&self) -> usize {
        0
        + self.data.iter().map(|s| 1 + sizeof_len((s).get_size())).sum::<usize>()
        + if self.seat == flights::Seat::ECONOMY { 0 } else { 1 + sizeof_varint(*(&self.seat) as u64) }
        + if self.passengers.is_empty() { 0 } else { 1 + sizeof_len(self.passengers.iter().map(|s| sizeof_varint(*(s) as u64)).sum::<usize>()) }
        + if self.trip == flights::Trip::ROUND_TRIP { 0 } else { 2 + sizeof_varint(*(&self.trip) as u64) }
    }

    fn write_message<W: WriterBackend>(&self, w: &mut Writer<W>) -> Result<()> {
        for s in &self.data { w.write_with_tag(26, |w| w.write_message(s))?; }
        if self.seat != flights::Seat::ECONOMY { w.write_with_tag(72, |w| w.write_enum(*&self.seat as i32))?; }
        w.write_packed_with_tag(66, &self.passengers, |w, m| w.write_enum(*m as i32), &|m| sizeof_varint(*(m) as u64))?;
        if self.trip != flights::Trip::ROUND_TRIP { w.write_with_tag(152, |w| w.write_enum(*&self.trip as i32))?; }
        Ok(())
    }
}

