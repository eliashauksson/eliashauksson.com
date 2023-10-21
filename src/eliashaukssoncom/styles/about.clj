(ns eliashaukssoncom.styles.about
  (:require [garden.core :refer [css]]
            [garden.units :refer [px vh vw]]
            [garden.color :refer [rgb]]
            [garden.stylesheet :refer [at-media]]
            [eliashaukssoncom.styles.colors :refer :all]))

(def about-style
  (css
   [:.about-content {:display "flex"
                     :justify-content "center"
                     :align-items "center"
                     :background-color bg-color
                     :min-height (vh 92)}]
   [:.profile-img {:width (px 600)
                   :height "auto"
                   :max-height (px 600)
                   :margin-left (px 20)
                   :margin-right (px 20)
                   :object-fit "contain"}]
   [:.about-right-container {:margin-left (px 30)}]
   [:.about-text {:flex "1"
                  :max-width (px 800)
                  :margin-right (px 20)
                  :margin-bottom (px 50)
                  :color fg-color}
    [:h1 {:font-size (px 36)
          :margin-bottom (px 10)}]
    [:p {:font-size (px 20)
         :line-height "1.5"}]]
   [:.about-footer
    [:p {:color fg-color
         :font-size (px 20)
         :margin-bottom (px 20)}]
    [:a {:text-decoration "none"
         :font-size (px 40)
         :padding (px 20)}
     [:.fa-github {:color (rgb 31 35 40)}]
     [:.fa-linkedin {:color (rgb 10 102 194)}]
     [:.fa-strava {:color (rgb 252 82 0)}]]]
   (at-media {:screen true
              :max-width (px 1000)
              :min-width (px 801)}
             [:.profile-img {:width (px 400)}])
   (at-media {:screen true
              :max-width (px 800)}
             [:.profile-img {:width (vw 80)
                             :max-width (px 600)
                             :margin-top (px 30)
                             :margin-bottom (px 40)}]
             [:.about-content {:justify-content "flex-start"
                               :flex-direction "column"}]
             [:.about-right-container {:margin-left (px 30)}])))
