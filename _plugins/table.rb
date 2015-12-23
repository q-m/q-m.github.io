# Monkey-patch Redcarpet to add the table class to tables
require 'redcarpet'
class Redcarpet::Render::HTML
  def table(header, body)
    "<table class=\"table table-hover\">" \
      "#{header}#{body}" \
    "</table>"
  end
end
