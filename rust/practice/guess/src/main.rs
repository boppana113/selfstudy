// // use std::cmp::Ordering;
// use rand::{Rng, RngExt};
// use std::{cmp::Ordering, io};

// fn main() {
//     println!("Guess a number 1-100:");
//     let mut rng = rand::rng();

//     let secret: u32 = rng.random_range(1..100);

//     loop {
//         let mut guess = String::new();

//         io::stdin()
//             .read_line(&mut guess)
//             .expect("failed to read a line");

//         let guess: u32 = guess.trim().parse().expect("type a number"); //shadowing

//         println!("You guessed {guess}");

//         match guess.cmp(&secret) {
//             Ordering::Less => println!("too small"),
//             Ordering::Greater => println!("too big"),
//             Ordering::Equal => {
//                 println!("you win");
//                 break;
//             }
//         }
//     }
// }
fn cost(tokens: u32, price_per_million: f64) -> f64 {
    tokens as f64 / 1_000_000.0 * price_per_million
}

fn main() {
    const MAX_TOKENS: u32 = 200000;
    let x = 5;
    let x = x + 1;

    println!("Before the brackets: {x}");
    {
        let x = x * 2;
        println!("Within the brackets: {x}");
    }
    println!("After the brackets: {x}");
    println!("Max tokens {MAX_TOKENS}");

    let s = "42";
    let s: u32 = s.parse().unwrap();
    println!("s = {s}");

    let pair: (f64, f64) = (3.0, 15.0);
    let (input_price, output_price) = pair;
    let first = pair.0;
    let arr = [1, 2, 3]; // array: fixed length
    let mut v = vec![4, 5, 6];

    let input_tokens: u32 = 500_000;
    let output_tokens: u32 = 100_000_000;
    let total_cost: f64 = cost(input_tokens, pair.0) + cost(output_tokens, pair.1);
    println!("total cost = {total_cost}");
    let tokens = 10_000;
    let label = if tokens > 100_000 { "big" } else { "small" };

    println!("{:?}", arr);
    println!("{:#?}", v);

    v.push(7);
    println!("{:#?}", v);
    let mut a = [0; 5];

    for i in 0..5 {
        a[i] = i * i;
    }
    println!("{:#?}", a);

    for (i, x) in a.iter_mut().enumerate() {
        *x = i * i * i;
    }
    println!("{:#?}", a);
}
