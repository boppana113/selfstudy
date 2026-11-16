use std::io;

fn main() {
    println!("Guess a number 1-100:");

    let mut guess = String::new();

    io::stdin()
        .read_line(&mut guess)
        .expect("failed to read line");

    let guess: u32 = guess.trim().parse().expect("type a number");
    println!("You guessed {guess}");
}
