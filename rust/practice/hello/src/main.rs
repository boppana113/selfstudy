use std::io;

const SECRET_NUMBER: u32 = 50;

fn compare_guess(guess: u32) {
    if guess < 50 {
        println!("too low")
    } else if guess > 50 {
        println!("too high")
    } else {
        println!("Correct!")
    }
}

fn identity_plus_one(guess: u32) -> u32 {
    guess + 1
}

fn add_one(guess: &mut u32) -> () {
    // modify the value
    *guess += 1;
}

fn main() {
    println!("Guess a number 1-100:");

    let mut guess = String::new();

    io::stdin()
        .read_line(&mut guess)
        .expect("failed to read line");

    let mut guess: u32 = guess.trim().parse().expect("type a number");
    println!("You guessed {guess}");

    compare_guess(guess);
    println!("identity_plus_one = {}", identity_plus_one(guess));

    add_one(&mut guess);
    println!("add_one = {}", guess);
}
