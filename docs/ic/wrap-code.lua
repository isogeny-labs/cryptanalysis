-- Wrap long literal identifiers in PDF tables without changing their text.
function Code(el)
  if FORMAT:match('latex') and #el.text > 20 and el.text:match('^[%w%._/%-]+$') then
    local parts = {}
    for char in el.text:gmatch('.') do
      if char == '_' then char = '\\_' end
      table.insert(parts, char .. '\\allowbreak{}')
    end
    return pandoc.RawInline('latex', '\\texttt{' .. table.concat(parts) .. '}')
  end
end

function Str(el)
  if FORMAT:match('latex') and el.text:match('%d%d%d%d%d%d%d%d%d%d%d') then
    local latex = pandoc.write(pandoc.Pandoc({pandoc.Plain({el})}), 'latex')
    latex = latex:gsub('%d%d%d%d%d%d%d%d%d%d%d+', function(number)
      return number:gsub('.', function(char) return char .. '\\allowbreak{}' end)
    end)
    return pandoc.RawInline('latex', latex)
  end
end
