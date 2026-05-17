
const std = @import("std");

pub const NodeType = enum(u8) {
    PART = 0,
    TITLE = 1,
    CHAPTER = 2,
    SECTION = 3,
    SUBSECTION = 4,
    ARTICLE = 5,
    CONTENT = 6,
};

export fn build_ast(stream_ptr: [*]const u8, len: usize) i32 {
    if (len == 0) return 0;
    
    const data = stream_ptr[0..len];
    var node_count: i32 = 0;
    
    var i: usize = 0;
    while (i < len - 10) : (i += 1) {
        // Scan for structural keywords in English stream
        if (std.mem.eql(u8, data[i..i+4], "PART")) {
            node_count += 1;
            i += 4;
        } else if (std.mem.eql(u8, data[i..i+7], "CHAPTER")) {
            node_count += 1;
            i += 7;
        } else if (std.mem.eql(u8, data[i..i+7], "Section")) {
            node_count += 1;
            i += 7;
        } else if (std.mem.eql(u8, data[i..i+7], "Article")) {
            node_count += 1;
            i += 7;
        }
    }

    return node_count;
}
