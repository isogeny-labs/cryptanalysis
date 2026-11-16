use serde_json::{Value,json};
use std::{collections::BTreeSet,env,fs};
fn walk(a:&Value,b:&Value,path:String,d:&mut Vec<Value>){
 if a==b{return}
 match(a,b){
 (Value::Object(x),Value::Object(y))=>{let keys:BTreeSet<_>=x.keys().chain(y.keys()).collect();for k in keys{match(x.get(k),y.get(k)){(Some(u),Some(v))=>walk(u,v,format!("{path}.{k}"),d),_=>d.push(json!({"path":format!("{path}.{k}"),"expected":x.get(k),"actual":y.get(k)}))}}},
 (Value::Array(x),Value::Array(y))=>{if x.len()!=y.len(){d.push(json!({"path":format!("{path}.length"),"expected":x.len(),"actual":y.len()}));}for(i,(u,v))in x.iter().zip(y.iter()).enumerate(){walk(u,v,format!("{path}[{i}]"),d)}},
 _=>d.push(json!({"path":path,"expected":a,"actual":b}))
 }
}
fn main(){let args:Vec<_>=env::args().collect();assert_eq!(args.len(),4);let a:Value=serde_json::from_slice(&fs::read(&args[1]).unwrap()).unwrap();let b:Value=serde_json::from_slice(&fs::read(&args[2]).unwrap()).unwrap();let mut d=Vec::new();walk(&a,&b,"$".into(),&mut d);fs::write(&args[3],serde_json::to_vec_pretty(&json!({"all_literal_differences":d,"scope":"whole structural literal comparison; no fields excluded"})).unwrap()).unwrap();println!("literal differences: {}",d.len());for v in d.iter().take(12){println!("{}",v);}}
