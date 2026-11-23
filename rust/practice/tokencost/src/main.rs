// tokencost: print the cost of an LLM call from a hard-coded price table.
//
//   cargo run -- claude-sonnet 1200 350
//   => claude-sonnet: 1200 in + 350 out = $0.008850
//
// Prices are USD per million tokens:
//   claude-haiku   in 1.00   out 5.00
//   claude-sonnet  in 3.00   out 15.00
//   claude-opus    in 5.00   out 25.00

fn main() {
    // TODO 1: collect std::env::args() into a Vec<String>.
    //         Print it once with {:?} to see what index 0 is.

    // TODO 2: if the argument count is wrong, print
    //         "usage: tokencost <model> <input_tokens> <output_tokens>"
    //         and std::process::exit(1).

    // TODO 3: parse the two token counts with .parse::<u32>().
    //         Start with .unwrap(), then try passing "abc" and read the panic.

    // TODO 4: call prices() and cost(), then print the result
    //         with 6 decimal places ({:.6}).
}

/// Returns (input_price, output_price) in USD per million tokens.
fn prices(model: &str) -> (f64, f64) {
    // TODO 5: match on model. For an unknown model, print an error
    //         that lists the valid models and exit(1).
    todo!("match on {model}")
}

/// Returns the total cost in USD.
fn cost(input: u32, output: u32, in_price: f64, out_price: f64) -> f64 {
    // TODO 6: input * in_price / 1_000_000 + output * out_price / 1_000_000
    //         (the compiler will make you cast with `as f64`).
    todo!("{input} {output} {in_price} {out_price}")
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
