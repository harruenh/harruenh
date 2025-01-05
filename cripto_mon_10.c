#include <gtk/gtk.h>
#include <curl/curl.h>
#include <json-c/json.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>

#define MAX_PAIRS 10
#define API_URL "https://api.binance.com/api/v3/ticker/price?symbol="

typedef struct {
    char pair[20];
    double previous_price;
    GtkWidget *label;
} CryptoPair;

CryptoPair selected_pairs[MAX_PAIRS];
int selected_count = 0;
int running = 1;

// Callback to handle API response
size_t write_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    strcat((char *)userp, (char *)contents);
    return size * nmemb;
}

// Fetch price from Binance API
double fetch_price(const char *pair) {
    CURL *curl;
    CURLcode res;
    char url[256];
    char response[4096] = "";
    snprintf(url, sizeof(url), "%s%s", API_URL, pair);

    curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, response);
        res = curl_easy_perform(curl);
        curl_easy_cleanup(curl);

        if (res == CURLE_OK) {
            struct json_object *parsed_json;
            struct json_object *price_obj;
            parsed_json = json_tokener_parse(response);
            if (json_object_object_get_ex(parsed_json, "price", &price_obj)) {
                return atof(json_object_get_string(price_obj));
            }
        }
    }
    return -1.0;
}

// Update prices in the background
void *update_prices(void *arg) {
    while (running) {
        for (int i = 0; i < selected_count; i++) {
            double current_price = fetch_price(selected_pairs[i].pair);
            if (current_price > 0) {
                double change = 0;
                if (selected_pairs[i].previous_price > 0) {
                    change = ((current_price - selected_pairs[i].previous_price) / selected_pairs[i].previous_price) * 100;
                }
                selected_pairs[i].previous_price = current_price;

                char label_text[256];
                snprintf(label_text, sizeof(label_text), "%s: %.2f (%.2f%%)", selected_pairs[i].pair, current_price, change);
                gtk_label_set_text(GTK_LABEL(selected_pairs[i].label), label_text);
            } else {
                gtk_label_set_text(GTK_LABEL(selected_pairs[i].label), "Error fetching price");
            }
        }
        sleep(10);
    }
    return NULL;
}

// Confirm selection of pairs
void confirm_selection(GtkWidget *widget, gpointer data) {
    GtkWidget *listbox = GTK_WIDGET(data);
    GList *rows = gtk_container_get_children(GTK_CONTAINER(listbox));

    selected_count = 0;
    for (GList *row = rows; row != NULL && selected_count < MAX_PAIRS; row = row->next) {
        GtkWidget *row_child = gtk_bin_get_child(GTK_BIN(row->data));
        const char *pair = gtk_entry_get_text(GTK_ENTRY(row_child));
        strncpy(selected_pairs[selected_count].pair, pair, sizeof(selected_pairs[selected_count].pair));
        selected_pairs[selected_count].previous_price = 0;

        selected_pairs[selected_count].label = gtk_label_new("Cargando...");
        gtk_box_pack_start(GTK_BOX(gtk_widget_get_parent(widget)), selected_pairs[selected_count].label, FALSE, FALSE, 5);
        gtk_widget_show(selected_pairs[selected_count].label);
        selected_count++;
    }
}

int main(int argc, char *argv[]) {
    gtk_init(&argc, &argv);

    // Main window
    GtkWidget *window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(window), "Crypto Price Monitor");
    gtk_window_set_default_size(GTK_WINDOW(window), 400, 600);
    g_signal_connect(window, "destroy", G_CALLBACK(gtk_main_quit), NULL);

    // Main layout
    GtkWidget *vbox = gtk_box_new(GTK_ORIENTATION_VERTICAL, 5);
    gtk_container_add(GTK_CONTAINER(window), vbox);

    // Listbox for pair entry
    GtkWidget *listbox = gtk_list_box_new();
    for (int i = 0; i < MAX_PAIRS; i++) {
        GtkWidget *entry = gtk_entry_new();
        gtk_list_box_insert(GTK_LIST_BOX(listbox), entry, -1);
    }
    gtk_box_pack_start(GTK_BOX(vbox), listbox, TRUE, TRUE, 5);

    // Confirm button
    GtkWidget *confirm_button = gtk_button_new_with_label("Confirmar Selecci\u00f3n");
    g_signal_connect(confirm_button, "clicked", G_CALLBACK(confirm_selection), listbox);
    gtk_box_pack_start(GTK_BOX(vbox), confirm_button, FALSE, FALSE, 5);

    // Show window
    gtk_widget_show_all(window);

    // Background thread for updating prices
    pthread_t update_thread;
    pthread_create(&update_thread, NULL, update_prices, NULL);

    gtk_main();

    running = 0;
    pthread_join(update_thread, NULL);

    return 0;
}
