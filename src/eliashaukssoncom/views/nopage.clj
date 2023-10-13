(ns eliashaukssoncom.views.nopage
  (:require [eliashaukssoncom.views.base :refer [base]]))

(defn nopage-content []
  [:div.nopage-content
   [:h1 "Page not found!"]])

(defn nopage-page []
  (base (nopage-content)))
