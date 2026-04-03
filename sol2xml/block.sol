class Main : Object {
    run [
        | b := [ :x | r := x plus: 10. ].
          result := b value: 5.
          str := result asString.
          _ := str print.
    ]
}
