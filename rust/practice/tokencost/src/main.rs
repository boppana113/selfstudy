// tokencost: print the cost of an LLM call from a hard-coded price table.
//
//   cargo run -- claude-sonnet 1200 350
//   => claude-sonnet: 1200 in + 350 out = $0.008850
//
// Prices are USD per million tokens:
//   claude-haiku   in 1.00   out 5.00
//   claude-sonnet  in 3.00   out 15.00
//   claude-opus    in 5.00   out 25.00

use std::env;

fn main() {
    // TODO 1: collect std::env::args() into a Vec<String>.
    //         Print it once with {:?} to see what index 0 is.
    let args: Vec<String> = env::args().collect();
    println!("{:?}", args);

    // TODO 2: if the argument count is wrong, print
    //         "usage: tokencost <model> <input_tokens> <output_tokens>"
    //         and std::process::exit(1).
    if args.len() != 4 {
        println!("usage: tokencost <model> <input_tokens> <output_tokens>");
        std::process::exit(1);
    }

    // TODO 3: parse the two token counts with .parse::<u32>().
    //         Start with .unwrap(), then try passing "abc" and read the panic.
    let input_tokens: u32 = args[2].parse().unwrap();
    let output_tokens: u32 = args[3].parse().unwrap();

    // TODO 4: call prices() and cost(), then print the result
    //         with 6 decimal places ({:.6}).
    let (input_price, output_price) = prices(&args[1]);
    let total_cost: f64 = cost(input_tokens, output_tokens, input_price, output_price);

    println!("total cost = {:.6}", total_cost);
}

/// Returns (input_price, output_price) in USD per million tokens.
fn prices(model: &str) -> (f64, f64) {
    // TODO 5: match on model. For an unknown model, print an error
    //         that lists the valid models and exit(1).
    // todo!("match on {model}")
    if model == "claude-haiku" {
        (1.00, 5.00)
    } else if model == "claude-sonnet" {
        (3.00, 15.00)
    } else if model == "claude-opus" {
        (5.00, 25.00)
    } else {
        println!("Valid models include claude-haiku, claude-sonnet, claude-opus");
        std::process::exit(1);
    }
    // Prices are USD per million tokens:
    //   claude-haiku   in 1.00   out 5.00
    //   claude-sonnet  in 3.00   out 15.00
    //   claude-opus    in 5.00   out 25.00
}

/// Returns the total cost in USD.
fn cost(input: u32, output: u32, in_price: f64, out_price: f64) -> f64 {
    // TODO 6: input * in_price / 1_000_000 + output * out_price / 1_000_000
    //         (the compiler will make you cast with `as f64`).
    // todo!("{input} {output} {in_price} {out_price}")
    (input as f64 * in_price + output as f64 * out_price) / 1_000_000.0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sonnet_cost() {
        // TODO 7: assert cost(...) equals a number you worked out by hand.
        //         Floats aren't exact, so check (actual - expected).abs() < 1e-9.
        let _ = cost;
        let _ = prices;
        todo!()
    }
}
