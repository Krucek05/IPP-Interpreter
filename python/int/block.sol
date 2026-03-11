class Main : Object {
    run [
        | a := self foo: 4.          "a = instance 14"
          b := [ :x | _ := 42. ].   "b = instance Block"
          c := b value: 16.          "c = instance 42"
          d := 'ahoj' print.         "d = instance 'ahoj' - print returns self"
    ]

    foo: [ :x |
        "variable 'u' is not used further, but the result of 'plus:' is returned
         as the return value of method 'foo:'"
        u := x plus: 10.
    ]
}
