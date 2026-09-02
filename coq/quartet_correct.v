(* QUARTET — Coq correctness: decrypt(encrypt(p,k),k)=p for ALL keys and
   plaintexts.

   This replaces the earlier placeholder (forall p k, True). The theorem
   below is a structural proof: each round function is invertible, so the
   roundtrip telescopes symbolically for every key and every plaintext.
   No enumeration over the 2^80 (key, plaintext) space is needed.

   The definitions mirror cipher.py exactly (S-box, FullMix M and its
   inverse M^3, per-round key add, key schedule rkey[i], round order).

   Compile: coqc quartet_correct.v
   (Coq 8.13+; verified with coqorg/coq:8.18)
*)

Require Import Arith List PeanoNat.
Import ListNotations.

(* ---------------------------------------------------------------- nibble *)
(* 4-bit words as a finite inductive, so every function is decidable.   *)

Inductive nib : Set :=
| N0 | N1 | N2 | N3 | N4 | N5 | N6 | N7
| N8 | N9 | N10 | N11 | N12 | N13 | N14 | N15.

Definition to_nat (n : nib) : nat :=
  match n with
  | N0 => 0 | N1 => 1 | N2 => 2 | N3 => 3 | N4 => 4 | N5 => 5
  | N6 => 6 | N7 => 7 | N8 => 8 | N9 => 9 | N10 => 10 | N11 => 11
  | N12 => 12 | N13 => 13 | N14 => 14 | N15 => 15
  end.

Definition of_nat (x : nat) : nib :=
  match x with
  | 0 => N0 | 1 => N1 | 2 => N2 | 3 => N3 | 4 => N4 | 5 => N5
  | 6 => N6 | 7 => N7 | 8 => N8 | 9 => N9 | 10 => N10 | 11 => N11
  | 12 => N12 | 13 => N13 | 14 => N14 | _ => N15
  end.

(* XOR on 4-bit words (low 4 bits of nat XOR), matches cipher.py "w ^ rk". *)
Definition xor_nib (a b : nib) : nib :=
  of_nat (Nat.land (Nat.lxor (to_nat a) (to_nat b)) 15).

(* PRESENT S-box and inverse (cipher.py SBOX / INV_SBOX). *)
Definition sbox_nib (x : nib) : nib :=
  match x with
  | N0 => N12 | N1 => N5 | N2 => N6 | N3 => N11 | N4 => N9 | N5 => N0
  | N6 => N10 | N7 => N13 | N8 => N3 | N9 => N14 | N10 => N15 | N11 => N8
  | N12 => N4 | N13 => N7 | N14 => N1 | N15 => N2
  end.

Definition inv_sbox_nib (x : nib) : nib :=
  match x with
  | N0 => N5 | N1 => N14 | N2 => N15 | N3 => N8 | N4 => N12 | N5 => N1
  | N6 => N2 | N7 => N13 | N8 => N11 | N9 => N4 | N10 => N6 | N11 => N3
  | N12 => N0 | N13 => N7 | N14 => N9 | N15 => N10
  end.

Lemma xor_nib_self_r : forall x r, xor_nib (xor_nib x r) r = x.
Proof.
  intros r x; destruct r; destruct x; reflexivity.
Qed.

Lemma inv_sbox_nib_sbox_nib : forall x, inv_sbox_nib (sbox_nib x) = x.
Proof.
  intros x; destruct x; reflexivity.
Qed.

(* ---------------------------------------------------------------- state *)
(* 16-bit state = four nibbles (w0 most significant), as in cipher.py.
   Nested right, matching the tuple notation in constructors/patterns. *)
Definition state := (nib * (nib * (nib * nib)))%type.

Definition xor_each (rk : nib) (st : state) : state :=
  match st with
  | (a, (b, (c, d))) => (xor_nib a rk, (xor_nib b rk, (xor_nib c rk, xor_nib d rk)))
  end.

Definition sbox_state (st : state) : state :=
  match st with
  | (a, (b, (c, d))) => (sbox_nib a, (sbox_nib b, (sbox_nib c, sbox_nib d)))
  end.

Definition inv_sbox_state (st : state) : state :=
  match st with
  | (a, (b, (c, d))) => (inv_sbox_nib a, (inv_sbox_nib b, (inv_sbox_nib c, inv_sbox_nib d)))
  end.

(* FullMix matrix M (SPEC sec 4 / cipher.py linear_layer):
     W0' = w0^w1^w2, W1' = w1^w2^w3, W2' = w2^w3^w0, W3' = w3^w0^w1 *)
Definition fullmix (st : state) : state :=
  match st with
  | (a, (b, (c, d))) =>
      (xor_nib a (xor_nib b c),
       (xor_nib b (xor_nib c d),
        (xor_nib c (xor_nib d a), xor_nib d (xor_nib a b))))
  end.

(* Inverse FullMix = M^3 (cipher.py inv_linear_layer):
     W0' = w0^w2^w3, W1' = w0^w1^w3, W2' = w0^w1^w2, W3' = w1^w2^w3 *)
Definition inv_fullmix (st : state) : state :=
  match st with
  | (a, (b, (c, d))) =>
      (xor_nib a (xor_nib c d),
       (xor_nib a (xor_nib b d),
        (xor_nib a (xor_nib b c), xor_nib b (xor_nib c d))))
  end.

(* Machine-checked (exhaustive over the 2^16 states, by reflection . *)
Lemma inv_fullmix_fullmix : forall st, inv_fullmix (fullmix st) = st.
Proof.
  intros st; destruct st as [a [b [c d]]].
  destruct a; destruct b; destruct c; destruct d; reflexivity.
Qed.

Lemma inv_sbox_state_sbox_state : forall st, inv_sbox_state (sbox_state st) = st.
Proof.
  intros [a [b [c d]]]; simpl.
  now rewrite 4 inv_sbox_nib_sbox_nib.
Qed.

Lemma xor_each_xor_each : forall rk st, xor_each rk (xor_each rk st) = st.
Proof.
  intros rk [a [b [c d]]]; simpl.
  now rewrite 4 xor_nib_self_r.
Qed.

(* ---------------------------------------------------------------- round *)

(* One encryption round (cipher.py _round / _round_bitsliced):
     S-box layer, XOR rk into every nibble, FullMix. *)
Definition round (rk : nib) (st : state) : state :=
  fullmix (xor_each rk (sbox_state st)).

(* One decryption round (cipher.py _inv_round / _inv_round_bitsliced). *)
Definition inv_round (rk : nib) (st : state) : state :=
  inv_sbox_state (xor_each rk (inv_fullmix st)).

Lemma round_inv : forall rk st, inv_round rk (round rk st) = st.
Proof.
  intros rk st; unfold inv_round, round.
  rewrite inv_fullmix_fullmix.
 rewrite xor_each_xor_each.
  apply inv_sbox_state_sbox_state.
Qed.

(* ---------------------------------------------------------------- keyschedule *)

(* Key K is an opaque function of 16 nibbles: K j is the j-th key nibble
   (cipher.py key_nibbles[j] = (key >> 4j) & 0xF).
   rkey mirrors cipher.py _expand_key:
     rk[i] = K[i mod 16] xor (xor over j of sbox(K[j] xor ((i+j+1) mod 16)))
   ((k ^ (r+j+1)) & 0xF = k xor ((r+j+1) mod 16) for k < 16, as in Python.)
   For the roundtrip theorem the schedule needs no property beyond
   returning a nibble; it is defined here to match the reference exactly. *)
Definition rkey (i : nat) (K : nat -> nib) : nib :=
  fold_right xor_nib (K (Nat.modulo i 16))
    (map (fun j => sbox_nib (xor_nib (K j) (of_nat (Nat.modulo (i + j + 1) 16))))
         (seq 0 16)).

Definition rk_list (n : nat) (K : nat -> nib) : list nib :=
  map (fun i => rkey i K) (seq 0 n).

(* ---------------------------------------------------------------- encrypt/decrypt *)

Fixpoint iter_rounds (rks : list nib) (st : state) : state :=
  match rks with
  | [] => st
  | rk :: rks' => iter_rounds rks' (round rk st)
  end.

Fixpoint iter_inv_rounds (rks : list nib) (st : state) : state :=
  match rks with
  | [] => st
  | rk :: rks' => iter_inv_rounds rks' (inv_round rk st)
  end.

(* encrypt: rounds 0..15 in order; decrypt: inv rounds 15..0 (reversed). *)
Definition encrypt (K : nat -> nib) (p : state) : state :=
  iter_rounds (rk_list 16 K) p.

Definition decrypt (K : nat -> nib) (c : state) : state :=
  iter_inv_rounds (rev (rk_list 16 K)) c.

(* ---------------------------------------------------------------- proof *)

Lemma iter_inv_rounds_app : forall (l1 l2 : list nib) st,
  iter_inv_rounds (l1 ++ l2) st = iter_inv_rounds l2 (iter_inv_rounds l1 st).
Proof.
  intros l1; induction l1 as [| a l1' IH]; intros l2 st.
  - reflexivity.
  - simpl. rewrite IH. reflexivity.
Qed.

Lemma iter_inv_rounds_rev_iter_rounds :
  forall (rks : list nib) st,
    iter_inv_rounds (rev rks) (iter_rounds rks st) = st.
Proof.
  intros rks; induction rks as [| rk rks' IH]; intros st.
  - reflexivity.
  - simpl.
    rewrite iter_inv_rounds_app.
    simpl.
    rewrite IH.
    apply round_inv.
Qed.

Theorem quartet_roundtrip : forall (K : nat -> nib) (p : state),
  decrypt K (encrypt K p) = p.
Proof.
  intros K p. unfold decrypt, encrypt.
  apply iter_inv_rounds_rev_iter_rounds.
Qed.