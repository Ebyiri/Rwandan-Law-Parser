
const std = @import("std");

pub const NodeType = enum(u8) {
    BOOK = 0, PART = 1, TITLE = 2, CHAPTER = 3, SECTION = 4, ARTICLE = 5, CONTENT = 6,
};

const Node = struct {
    id: usize,
    parent_id: i32,
    node_type: NodeType,
    number: []const u8,
    index: usize,
};

fn toUpper(c: u8) u8 {
    if (c >= 'a' and c <= 'z') return c - 32;
    return c;
}

fn manualMatch(data: []const u8, pattern: []const u8) bool {
    if (data.len < pattern.len) return false;
    for (pattern, 0..) |p_char, i| {
        if (toUpper(data[i]) != toUpper(p_char)) return false;
    }
    return true;
}

fn extractNumber(data: []const u8) []const u8 {
    var j: usize = 0;
    while (j < data.len and (std.ascii.isWhitespace(data[j]) or data[j] == '.')) : (j += 1) {}
    var start = j;
    while (j < data.len and (std.ascii.isAlphanumeric(data[j]) or data[j] == '.')) : (j += 1) {
        if (data[j] == ':' or data[j] == ' ') break;
    }
    return data[start..j];
}

var output_buf: [1024 * 1024 * 30]u8 = undefined;

export fn build_ast(stream_ptr: [*]const u8, len: usize) [*]const u8 {
    const data = stream_ptr[0..len];
    var fba = std.heap.FixedBufferAllocator.init(&output_buf);
    const allocator = fba.allocator();
    var list = std.ArrayList(Node).init(allocator);

    var i: usize = 0;
    var last_parent: i32 = -1;

    while (i < data.len) {
        const slice = data[i..];

        if (manualMatch(slice, "PART") or manualMatch(slice, "IGICE") or manualMatch(slice, "PARTIE")) {
            list.append(.{ .id = list.items.len, .parent_id = -1, .node_type = .PART, .number = "", .index = i }) catch {};
            last_parent = @intCast(list.items.len - 1);
            i += 4; continue;
        }

        if (manualMatch(slice, "TITLE") or manualMatch(slice, "INTERURO") or manualMatch(slice, "TITRE")) {
            list.append(.{ .id = list.items.len, .parent_id = last_parent, .node_type = .TITLE, .number = "", .index = i }) catch {};
            last_parent = @intCast(list.items.len - 1);
            i += 5; continue;
        }

        if (manualMatch(slice, "CHAPTER") or manualMatch(slice, "UMUTWE") or manualMatch(slice, "CHAPITRE")) {
            list.append(.{ .id = list.items.len, .parent_id = last_parent, .node_type = .CHAPTER, .number = "", .index = i }) catch {};
            last_parent = @intCast(list.items.len - 1);
            i += 6; continue;
        }

        if (manualMatch(slice, "ARTICLE") or manualMatch(slice, "INGINGO")) {
            const is_kin = manualMatch(slice, "INGINGO");
            var offset: usize = if (is_kin) 7 else 7;
            
            if (is_kin) {
                var k = offset;
                while (k < slice.len and std.ascii.isWhitespace(slice[k])) : (k += 1) {}
                if (k + 2 <= slice.len and manualMatch(slice[k..k+2], "YA")) {
                    offset = k + 2;
                }
            }
            
            const num = extractNumber(slice[offset..]);
            list.append(.{ .id = list.items.len, .parent_id = last_parent, .node_type = .ARTICLE, .number = num, .index = i }) catch {};
            i += offset + num.len; continue;
        }
        i += 1;
    }

    var out_stream = std.ArrayList(u8).init(allocator);
    std.json.stringify(.{ .status = "success", .nodes = list.items }, .{}, out_stream.writer()) catch {};
    out_stream.append(0) catch {};
    return out_stream.items.ptr;
}
