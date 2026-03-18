class Daten < Formula
  include Language::Python::Virtualenv

  desc "Scaffold data science and ML projects with uv"
  homepage "https://github.com/henriquepmartins/daten"
  url "https://github.com/henriquepmartins/daten/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_GITHUB_ARCHIVE_SHA256"
  license "MIT"

  depends_on "python@3.12"
  depends_on "uv"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/daten --version")
  end
end
