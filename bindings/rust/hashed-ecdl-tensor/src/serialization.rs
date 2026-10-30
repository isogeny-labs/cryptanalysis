// JSON records use explicit fields without a derive/procedural-macro toolchain.
// This keeps the existing cryptanalysis supply-chain/licence policy unchanged.
// Missing, duplicate and unknown fields are rejected; only declared options default.
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
                struct RecordVisitor;
                impl<'de> serde::de::Visitor<'de> for RecordVisitor {
                    type Value = $name;

                    fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                        write!(formatter, "a {} object", stringify!($name))
                    }

                    fn visit_map<A: serde::de::MapAccess<'de>>(self, mut map: A) -> std::result::Result<Self::Value, A::Error> {
                        $(let mut $required = None;)*
                        $(let mut $optional = None;)*
                        while let Some(field) = map.next_key::<String>()? {
                            match field.as_str() {
                                $(stringify!($required) => {
                                    if $required.is_some() {
                                        return Err(serde::de::Error::duplicate_field(stringify!($required)));
                                    }
                                    $required = Some(map.next_value()?);
                                },)*
                                $(stringify!($optional) => {
                                    if $optional.is_some() {
                                        return Err(serde::de::Error::duplicate_field(stringify!($optional)));
                                    }
                                    $optional = Some(map.next_value()?);
                                },)*
                                _ => return Err(serde::de::Error::unknown_field(&field,
                                    &[$(stringify!($required),)* $(stringify!($optional),)*])),
                            }
                        }
                        Ok(Self::Value {
                            $($required: $required.ok_or_else(|| serde::de::Error::missing_field(stringify!($required)))?,)*
                            $($optional: $optional.unwrap_or_default(),)*
                        })
                    }
                }
                // Deserialize nested fields directly. A Value intermediary would
                // discard duplicate keys before their record visitor sees them.
                deserializer.deserialize_struct(stringify!($name),
                    &[$(stringify!($required),)* $(stringify!($optional),)*], RecordVisitor)
            }
        }
    };
}
