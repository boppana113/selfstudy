#[derive(Debug, Clone)]
struct ApiKey {
    id: u32,
    key: String,
    project_id: u32,
    user_id: Option<u32>,
}

impl ApiKey {
    fn new(id: u32, key: &str, project_id: u32) -> Self {
        // associated fn (no self), like a @classmethod
        ApiKey {
            id,
            key: key.to_string(),
            project_id,
            user_id: None,
        }
    }
    fn is_project(&self, p: u32) -> bool {
        self.project_id == p
    } // reads
    fn assign_user(&mut self, u: u32) {
        self.user_id = Some(u);
    } // changes it
    fn into_key(self) -> String {
        self.key
    } // consumes the struct
}

struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}

fn part1_drop() {
    let _a = Noisy("a");
    let _b: Noisy = Noisy("b");
    println!("end of scope");
}

fn take(k: &ApiKey) {
    println!("took {:?}", k);
}

// fn part1() {
//     let k = ApiKey {
//         id: 1,
//         key: String::from("sk-123"),
//     };
//     take(&k);
//     take(&k.clone());
//     println!("{}", k.id);

//     part1_drop();
// }

fn part2() {
    let mut keys = vec![String::from("sk-a"), String::from("sk-b")];
    let first = &keys[0];
    println!("{first}"); // correct
    keys.push(String::from("sk-c"));
    // println!("{first}"); // E0502: keys may have moved and rust prevents compilation if a previous expression statement mutate it

    let mut s = String::new();
    let a = &mut s;
    // let b = &mut s; // ← E0499
    a.push('x');
    // b.push('y');
}

fn is_live_key(key: &str) -> bool {
    key.starts_with("sk-live-")
}

fn part3() {
    let mut owned = String::from("sk-live-abc");
    owned.push_str("-sriram");
    println!("{owned}");
    println!("{}", is_live_key(&owned));
    let prefix: &str = &owned[0..7];
    println!("{prefix}");
}

struct Config {
    api_keys: Vec<ApiKey>,
}

impl Config {
    // lends: returns a borrow into self.api_keys, so it can't outlive the Config
    fn find_owned(&self, key: &str) -> Option<&ApiKey> {
        for k in &self.api_keys {
            // k: &ApiKey
            if k.key == key {
                // return Some(*k);
                // return Some(k.clone()); // this is a clone method
                return Some(k); // lend out the key: k is already a &ApiKey
            } // ← E0507 (cannot move out of *k, which is behind a shared reference
        }
        None
    }
}
fn main() {
    // part1();
    // part2();
    // part3();
    let mut k = ApiKey::new(1, "sk-abc", 42);

    println!("k.id = {}", k.id);
    let j = k.into_key();
    println!("k = {}", j);
}
