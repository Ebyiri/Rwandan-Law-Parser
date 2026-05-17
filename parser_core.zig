
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

fn caseInsensitiveMatch(data: []const u8, pattern: []const u8) bool {
    if (data.len < pattern.len) return false;
    for (pattern, 0..) |char, i| {
        const d = data[i];
        const upper_d = if (d >= 'a' and d <= 'z') d - 32 else d;
        const upper_p = if (char >= 'a' and char <= 'z') char - 32 else char;
        if (upper_d != upper_p) return false;
    }
    return true;
}

// Increased buffer to 2MB to ensure large laws like yours fit in the JSON output
var output_buf: [1024 * 2048]u8 = undefined;

export fn build_ast(stream_ptr: [*]const u8, len: usize) [*]const u8 {
    if (len == 0) return "{}";
    
    const data = stream_ptr[0..len];
    var fba = std.heap.FixedBufferAllocator.init(&output_buf);
    const allocator = fba.allocator();

    var list = std.ArrayList(struct { type: []const u8, index: usize }).init(allocator);
    
    var i: usize = 0;
    while (i < len - 10) : (i += 1) {
        if (caseInsensitiveMatch(data[i..], "PART ")) {
            list.append(.{ .type = "PART", .index = i }) catch {};
            i += 4;
        } else if (caseInsensitiveMatch(data[i..], "CHAPTER ")) {
            list.append(.{ .type = "CHAPTER", .index = i }) catch {};
            i += 7;
        } else if (caseInsensitiveMatch(data[i..], "Article ")) {
            list.append(.{ .type = "ARTICLE", .index = i }) catch {};
            i += 7;
        }
    }

    var out_stream = std.ArrayList(u8).init(allocator);
    std.json.stringify(.{ .detected_count = list.items.len, .nodes = list.items }, .{}, out_stream.writer()) catch {};
    out_stream.append(0) catch {}; // Null terminator for C-string interop
    
    return out_stream.items.ptr;
}
