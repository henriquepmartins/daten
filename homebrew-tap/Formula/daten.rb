class Daten < Formula
  include Language::Python::Virtualenv

  desc "Scaffold data science and ML projects with uv"
  homepage "https://pypi.org/project/daten/"
  url "https://files.pythonhosted.org/packages/source/d/daten/daten-0.1.0.tar.gz"
  sha256 "167560e437191e673b45b7175b0f629a5fc2d2ab7a32654674b2685ef474c1a4"
  license "MIT"

  depends_on "python@3.12"
  depends_on "uv"

  def install
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install_and_link buildpath
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/daten --version")
  end
end
