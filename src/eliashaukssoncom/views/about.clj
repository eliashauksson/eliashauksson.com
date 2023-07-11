(ns eliashaukssoncom.views.about
  (:require [markdown-to-hiccup.core :refer [file->hiccup]]
            [eliashaukssoncom.views.base :refer [base]]))

(defn about-content []
  [:div.about-content
   [:img.profile-img {:src "images/profile-image.jpg" :alt "Profile Picture"}]
   [:div.about-right-container
    [:div.about-text
     (file->hiccup "resources/public/markdown/about-me.md")]
    [:div.about-footer
     [:p "You can also find me on these platforms:"]
     [:a {:href "https://github.com/eliashauksson"}
      [:i {:class "fa-brands fa-github"}]]
     [:a {:href "https://www.linkedin.com/in/el%C3%ADas-hauksson-1939b31b8/"}
      [:i {:class "fa-brands fa-linkedin"}]]
     [:a {:href "https://www.strava.com/athletes/39041574"}
      [:i {:class "fa-brands fa-strava"}]]]]])

(defn about-page []
  (base about-content))
