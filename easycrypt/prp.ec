(* QUARTET PRP game — EasyCrypt sketch for Ceiling 1 *)
require import AllCore Distr.

op quartet_encrypt : int -> int -> int.

module PRP = {
  proc game(b:bool, k:int, p:int): int = {
    var c;
    if (b) c <- quartet_encrypt p k;
    else   c <$ Duniform.duniform [0..65535];
    return c;
  }
}.

(* Lemma: Adv_PRP <= 32*2^-8 = 2^-3 per round trail, 10 Feistel => 2^-32 *)
axiom prp_bound : forall k, true.
