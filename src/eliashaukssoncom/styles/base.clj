(ns eliashaukssoncom.styles.base
  (:require [garden.core :refer [css]]
            [garden.units :refer [px vh percent]]
            [garden.stylesheet :refer [at-media at-keyframes]]
            [eliashaukssoncom.styles.colors :refer :all]))

(def base-style
  (css
   [:* {:margin (px 0)
        :padding (px 0)
        :box-sizing "border-box"
        :font-family "'Montserrat', sans-serif"}]
   [:nav {:display "flex"
          :justify-content "space-between"
          :align-items "center"
          :min-height (vh 8)
          :background-color blue-color}]
   [:.logo {:padding-left (px 30)
            :letter-spacing (px 3)
            :font-size (px 26)}
    [:a {:color bg-color
         :text-decoration "none"}]]
   [:.nav-links {:display "flex"
                 :list-style "none"
                 :padding-right (px 40)}
    [:li {:padding-left (px 30)}
     [:a {:color bg-color
          :text-decoration "none"
          :font-weight "bold"
          :letter-spacing (px 1)
          :font-size (px 22)}]]]
   [:.burger {:display "none"
              :cursor "pointer"
              :padding-right (px 30)}
    [:div {:width (px 25)
           :height (px 3)
           :background-color bg-color
           :margin (px 5)
           :transition "all 0.3s ease"}]]
   (at-media {:screen true :max-width (px 800)}
             [:body {:overflow-x "hidden"}]
             [:.nav-links {:position "absolute"
                           :right (px 0)
                           :height (vh 92)
                           :top (vh 8)
                           :background-color blue-color
                           :display "flex"
                           :flex-direction "column"
                           :justify-content "space-around"
                           :align-items "center"
                           :width (percent 50)
                           :transform "translateX(100%)"
                           :transition "transform 0.5s ease-in"}
              [:li {:opacity 0}]]
             [:.burger {:display "block"}])
   [:.nav-active {:transform "translateX(0%)"}]
   (at-keyframes :navLinkFade
                 [[:from {:opacity 0
                          :transform "translateX(50px)"}
                   :to {:opacity 1
                        :transform "translateX(0px)"}]])
   [:.toggle
    [:.line1 {:transform "rotate(-45deg) translate(-5px, 6px)"}]
    [:.line2 {:opacity 0}]
    [:.line3 {:transform "rotate(45deg) translate(-5px, -6px)"}]]))
