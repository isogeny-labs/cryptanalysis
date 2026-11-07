// JSON records use explicit fields without a derive/procedural-macro toolchain.
// This keeps the existing cryptanalysis supply-chain/licence policy unchanged.
// Required fields and unknown fields are rejected; only declared options default.
macro_rules! json_record {
    ($name:ty, required { $($required:ident),* $(,)? }, optional { $($optional:ident),* $(,)? }) => {
        impl serde::Serialize for $name {
            fn serialize<S: serde::Serializer>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error> {
                let mut fields = serde_json::Map::new();
                $(fields.insert(stringify!($required).into(), serde_json::to_value(&self.$required)
                    .map_err(serde::ser::Error::custom)?);)*
                $(fields.insert(stringify!($optional).into(), serde_json::to_value(&self.$optional)
                    .map_err(serde::ser::Error::custom)?);)*
                serde::Serialize::serialize(&serde_json::Value::Object(fields), serializer)
            }
        }
        impl<'de> serde::Deserialize<'de> for $name {
            fn deserialize<D: serde::Deserializer<'de>>(deserializer: D) -> std::result::Result<Self, D::Error> {
                let mut fields = <serde_json::Map<String, serde_json::Value> as serde::Deserialize>::deserialize(deserializer)?;
                let record = Self {
                    $($required: serde_json::from_value(fields.remove(stringify!($required))
                        .ok_or_else(|| <D::Error as serde::de::Error>::missing_field(stringify!($required)))?)
                        .map_err(serde::de::Error::custom)?,)*
                    $($optional: match fields.remove(stringify!($optional)) {
                        Some(value) => serde_json::from_value(value).map_err(serde::de::Error::custom)?,
                        None => Default::default(),
                    },)*
                };
                if let Some(field) = fields.keys().next() {
                    return Err(serde::de::Error::custom(format!("unknown field {field}")));
                }
                Ok(record)
            }
        }
    };
}
