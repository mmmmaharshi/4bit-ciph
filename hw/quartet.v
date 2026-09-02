// QUARTET 16-bit block, 64-bit key, 16-round SPN
// RTL for Yosys synthesis - iterative enc-only core
// Mano H. | 2026

// PRESENT S-box: 0xC,5,6,B,9,0,A,D,3,E,F,8,4,7,1,2
module sbox4 (
    input  [3:0] a,
    output reg [3:0] y
);
    always @* begin
        case (a)
            4'h0: y = 4'hC; 4'h1: y = 4'h5; 4'h2: y = 4'h6; 4'h3: y = 4'hB;
            4'h4: y = 4'h9; 4'h5: y = 4'h0; 4'h6: y = 4'hA; 4'h7: y = 4'hD;
            4'h8: y = 4'h3; 4'h9: y = 4'hE; 4'hA: y = 4'hF; 4'hB: y = 4'h8;
            4'hC: y = 4'h4; 4'hD: y = 4'h7; 4'hE: y = 4'h1; 4'hF: y = 4'h2;
        endcase
    end
endmodule

// FullMix: W0'=W0^W1^W2, W1'=W1^W2^W3, W2'=W2^W3^W0, W3'=W3^W0^W1 (order 4: M^4=I, M^-1=M^3)
module fullmix (
    input  [15:0] din,
    output [15:0] dout
);
    wire [3:0] w0 = din[15:12];
    wire [3:0] w1 = din[11:8];
    wire [3:0] w2 = din[7:4];
    wire [3:0] w3 = din[3:0];
    assign dout = {w0 ^ w1 ^ w2, w1 ^ w2 ^ w3, w2 ^ w3 ^ w0, w3 ^ w0 ^ w1};
endmodule

// One combinational round: SBOX(4) + key XOR + FullMix
module quartet_round_comb (
    input  [15:0] state_in,
    input  [3:0]  rk,
    output [15:0] state_out
);
    wire [3:0] s0, s1, s2, s3;
    sbox4 u0 (.a(state_in[15:12]), .y(s0));
    sbox4 u1 (.a(state_in[11:8]),  .y(s1));
    sbox4 u2 (.a(state_in[7:4]),   .y(s2));
    sbox4 u3 (.a(state_in[3:0]),   .y(s3));

    wire [15:0] after_sbox_key = {s0 ^ rk, s1 ^ rk, s2 ^ rk, s3 ^ rk};

    fullmix fm (.din(after_sbox_key), .dout(state_out));
endmodule

// Iterative enc-only core: 1 round datapath + state reg + round counter
// For area estimation (GE) - the standard iterative lightweight metric
module quartet_enc_iterative (
    input         clk,
    input         rst,
    input         start,
    input  [15:0] plaintext,
    input  [63:0] key,
    output reg [15:0] ciphertext,
    output reg        done
);
    reg [15:0] state;
    reg [4:0]  round; // 0..16

    // round key: rk = K[round%16] XOR XOR_{j=0..15} SBOX[K[j] XOR (round+j+1)]
    // Implemented as combinational logic
    wire [3:0] rk;
    quartet_round_key rkg (.key(key), .round(round[3:0]), .rk(rk));

    wire [15:0] next_state;
    quartet_round_comb rnd (.state_in(state), .rk(rk), .state_out(next_state));

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= 16'h0;
            round <= 5'd0;
            done  <= 1'b0;
            ciphertext <= 16'h0;
        end else if (start) begin
            state <= plaintext;
            round <= 5'd0;
            done  <= 1'b0;
        end else if (round < 16) begin
            state <= next_state;
            round <= round + 1'b1;
            if (round == 15) begin
                ciphertext <= next_state;
                done <= 1'b1;
            end
        end
    end
endmodule

// Combinational round key generator
module quartet_round_key (
    input  [63:0] key,
    input  [3:0]  round,
    output [3:0]  rk
);
    // Extract 16 nibbles
    wire [3:0] k [0:15];
    genvar i;
    generate
        for (i = 0; i < 16; i = i + 1) begin : kn
            assign k[i] = key[4*i +: 4];
        end
    endgenerate

    // 16 S-box lookups (combinational)
    wire [3:0] s [0:15];
    generate
        for (i = 0; i < 16; i = i + 1) begin : sk
            sbox4 sxi (.a(k[i] ^ ((round + i + 1) & 4'hF)), .y(s[i]));
        end
    endgenerate

    // rk = k[round%16] ^ s[0]^s[1]^...^s[15]
    wire [3:0] xor_s = s[0] ^ s[1] ^ s[2] ^ s[3] ^ s[4] ^ s[5] ^ s[6] ^ s[7]
                     ^ s[8] ^ s[9] ^ s[10]^ s[11]^ s[12]^ s[13]^ s[14]^ s[15];
    assign rk = k[round] ^ xor_s;
endmodule

// Fully unrolled 16-round combinational (for throughput comparison)
module quartet_enc_unrolled (
    input  [15:0] plaintext,
    input  [63:0] key,
    output [15:0] ciphertext
);
    wire [15:0] s [0:16];
    wire [3:0]  rk [0:15];

    assign s[0] = plaintext;

    genvar r;
    generate
        for (r = 0; r < 16; r = r + 1) begin : rounds
            quartet_round_key rkg (.key(key), .round(r[3:0]), .rk(rk[r]));
            quartet_round_comb rnd (.state_in(s[r]), .rk(rk[r]), .state_out(s[r+1]));
        end
    endgenerate

    assign ciphertext = s[16];
endmodule
