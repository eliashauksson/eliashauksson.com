(defproject eliashaukssoncom "0.1.0-SNAPSHOT"
  :description "Elías' personal website."
  :dependencies [[org.clojure/clojure "1.11.1"]
                 [ring/ring-core "1.10.0"]
                 [ring/ring-jetty-adapter "1.10.0"]
                 [compojure "1.7.0"]
                 [hiccup "2.0.0-RC1"]
                 [garden "1.3.10"]
                 [markdown-to-hiccup "0.6.2"]]
  :paths ["src" "resources"]
  :main ^:skip-aot eliashaukssoncom.core)
